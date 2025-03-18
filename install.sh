#!/bin/bash

# Function to check if a command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Check if Go is installed
if ! command_exists go; then
    echo -e "\e[31mGo is not installed. Please install Go and rerun this script.\e[0m"
    exit 1
else
    echo -e "\e[1;32mGo is already installed.\e[0m"
fi

# Install waybackurls
go install github.com/tomnomnom/waybackurls@latest

# Install katana
go install github.com/projectdiscovery/katana/cmd/katana@latest

# Install cariddi
go install github.com/edoardottt/cariddi/cmd/cariddi@latest

# Install httpx
go install github.com/projectdiscovery/httpx/cmd/httpx@latest

# Install gf
go install github.com/tomnomnom/gf@latest

# Install dalfox
go install github.com/hahwul/dalfox/v2@latest

# Install Notify
go install github.com/projectdiscovery/notify/cmd/notify@latest

echo -e "\e[1;32mInstallation complete.\e[0m"