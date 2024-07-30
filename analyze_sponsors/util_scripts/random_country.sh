#!/bin/bash

countries=(
  "Albania" "Andorra" "Armenia" "Austria" "Belgium" "Bosnia & Herzegovina" "Bulgaria" "Croatia" "Cyprus" "Czechia" "Denmark" "Estonia" "Finland" "France" "Australia" "India"
  "Georgia" "Germany" "Greece" "Greenland" "Hungary" "Iceland" "Ireland" "Isle of Man" "Italy" "Latvia" "Liechtenstein" "Lithuania" "Luxembourg" "Malta" "Moldova" "Monaco" "Montenegro" "Netherlands"
  "North Macedonia" "Norway" "Poland" "Portugal" "Romania" "Serbia" "Slovakia" "Slovenia" "Spain" "Sweden" "Switzerland" "Ukraine" "United Kingdom" "turkey"
  "Algeria" "Egypt" "Ghana" "Israel" "Morocco" "Nigeria" "Saudi Arabia" "South Africa" "United Arab Emirates" "Azerbaijan" "Bangladesh" "Bhutan"
  "Brunei" "Cambodia" "Hong Kong" "Indonesia" "Japan" "Kazakhstan" "Laos" "Macau SAR China" "Malaysia" "Mongolia" "Nepal" "New Zealand" "Philippines"
  "Singapore" "South Korea" "Sri Lanka" "Taiwan" "Thailand" "Uzbekistan"
)

random_country=${countries[$RANDOM % ${#countries[@]}]}
echo -n "$random_country" | xclip -selection clipboard
echo "Copied '$random_country' to clipboard using xclip."
