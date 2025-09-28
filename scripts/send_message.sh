# Use with caution: telegram has blocked accounts for spamming
function send_message() {
    local token=$1;
    local chat_id=$2;
    local text=$3;
    
    data=$( \
        jq -n \
        --arg chat_id "$chat_id" \
        --arg text "$text" \
        '{
        "chat_id": $chat_id,
        "text": $text
        }'
    )

    response=$( \
        curl --silent\
        --location "https://api.telegram.org/bot$token/sendMessage" \
        --header "Content-Type: application/json" \
        --data "$data"
    )
}