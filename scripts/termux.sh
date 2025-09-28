#!/bin/bash

cd "$(dirname "$0")";

if [ -f count.txt ]; then
    prev_count=$(cat count.txt);
else
    prev_count=0;
fi

response=$( \

    curl --silent \
    --location 'https://www.property24.com/search/counter' \
    -H 'content-type: application/json;' \
    --data-raw '{"bedrooms":0,"bathrooms":0,"availability":0,"rentalRates":[],"sizeFrom":{"isCustom":false,"value":null},"sizeTo":{"isCustom":false,"value":null},"erfSizeFrom":{"isCustom":false,"value":null},"erfSizeTo":{"isCustom":false,"value":null},"floorSizeFrom":{"isCustom":false,"value":null},"floorSizeTo":{"isCustom":false,"value":null},"parkingType":1,"parkingSpaces":0,"hasFlatlet":null,"hasGarden":null,"hasPool":null,"furnishedStatus":2,"isPetFriendly":null,"isRepossessed":null,"isRetirement":null,"isInSecurityEstate":null,"onAuction":null,"onShow":null,"propertyTypes":[4,5,6],"autoCompleteItems":[{"id":459,"name":"Stellenbosch","parentId":null,"parentName":"Western Cape","type":2,"source":0,"normalizedName":"stellenbosch"}],"searchContextType":1,"priceFrom":{"isCustom":false,"value":null},"priceTo":{"isCustom":false,"value":null},"searchType":1,"sortOrder":0,"developmentSubType":0}' \
    --compressed

);

count=$(echo $response | jq '.count');
echo $count > count.txt;

if [ $count -ne $prev_count ]; then
    message="Change in count: $count";
    echo "$message";
else
    echo "No change in count. Exiting.";
    exit 1;
fi


echo "Number of properties: $count" ;

pages=$(( $count / 20 ));


if ((count % 20 > 0)); then
    pages=$(( $pages + 1 ))
fi

echo "Number of pages: $pages";

file="listing.txt"
old_file="old.txt"
new_file="new.txt"
base_url="https://www.property24.com"
total=0

cat $file > $old_file;
cat /dev/null > $file;
cat /dev/null > $new_file;

for ((page=1; page<=pages; page++)); do
    echo "Processing page: $page";

    response=$(

        curl --silent \
        --location "https://www.property24.com/to-rent/stellenbosch/western-cape/459/p$page?PropertyCategory=House%2cApartmentOrFlat%2cTownhouse"

    )

    first_list=$(grep -o 'data-listing-number="[0-9]*"' <<< "$response" | cut -d '"' -f 2)

    response=$(

        curl --silent \
        --location "https://www.property24.com/to-rent/stellenbosch/western-cape/459/p$page?PropertyCategory=House%2cApartmentOrFlat%2cTownhouse"

    )

    second_list=$(grep -o 'data-listing-number="[0-9]*"' <<< "$response" | cut -d '"' -f 2)

    array1=( $first_list )
    array2=( $second_list )
    common_numbers=()

    for num1 in "${array1[@]}"; do
        for num2 in "${array2[@]}"; do
            if [[ "$num1" = "$num2" ]]; then
                if [[ ! " ${common_numbers[@]} " =~ " $num1 " ]]; then
                    common_numbers+=("$num1")
                fi
                break
            fi
        done
    done

    i=0;
    for number in "${common_numbers[@]}" ; do
        url=$base_url$( grep "/to-rent/.*/$number" <<< "$response" | cut -d '"' -f 2)
        echo $url >> $file
        i=$(($i + 1))
    done
    total=$(($total+$i))
    echo "Total: $total, count: $i"

done

if [[ ! "$total" = "$count" ]]; then
    echo "Count is wrong";
else
    echo "All properties processed";
    old_urls=($(cat old.txt))
    new_urls=($(cat listing.txt))

    newly_added_urls=()
    for url in "${new_urls[@]}"; do
        if [[ ! " ${old_urls[@]} " =~ " $url " ]]; then
            newly_added_urls+=("$url")
        fi
    done

    if [[ ${#newly_added_urls[@]} -gt 0 ]]; then
        echo "Newly added URLs:";
        echo "${newly_added_urls[@]}";
        url="${newly_added_urls[@]}";
        action="termux-open-url $url";

        termux-notification \
        --title "Property24" \
        --content "$url" \
        --button1 "Open" \
        --button1-action "$action" \
        --id "p24$url";


        termux-open-url "$url";
        echo "${newly_added_urls[@]}" >> "$new_file"
    else
        echo "No newly added URLs found.";
    fi
fi