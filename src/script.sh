#!/bin/bash

if [ -f count.txt ]; then
    prev_count=$(cat count.txt);
else
    prev_count=0;
    echo "Container running for the first time. Creating count.txt file with value 0";
fi

while true; do

    response=$( \

        curl --silent \
        --location 'https://www.property24.com/search/counter' \
        -H 'content-type: application/json;' \
        --data-raw '{"bedrooms":0,"bathrooms":0,"availability":0,"rentalRates":[],"sizeFrom":{"isCustom":false,"value":null},"sizeTo":{"isCustom":false,"value":null},"erfSizeFrom":{"isCustom":false,"value":null},"erfSizeTo":{"isCustom":false,"value":null},"floorSizeFrom":{"isCustom":false,"value":null},"floorSizeTo":{"isCustom":false,"value":null},"parkingType":1,"parkingSpaces":0,"hasFlatlet":null,"hasGarden":null,"hasPool":null,"furnishedStatus":2,"isPetFriendly":null,"isRepossessed":null,"isRetirement":null,"isInSecurityEstate":null,"onAuction":null,"onShow":null,"propertyTypes":[4,5,6],"autoCompleteItems":[{"id":459,"name":"Stellenbosch","parentId":null,"parentName":"Western Cape","type":2,"source":0,"normalizedName":"stellenbosch"}],"searchContextType":1,"priceFrom":{"isCustom":false,"value":null},"priceTo":{"isCustom":false,"value":null},"searchType":1,"sortOrder":0,"developmentSubType":0}' \
        --compressed

    );

    count=$(echo $response | jq '.count');

    if [ $? -ne 0 ]; then
        echo "Error: Failed to parse response";
        break;
    fi

    echo $count;
    echo $count > count.txt;

    sleep 1;

done