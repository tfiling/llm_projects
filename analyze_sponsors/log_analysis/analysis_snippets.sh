#pipe for extracting log parts:
#| cut -d'|' -f2,3 | sort | uniq

#Copy to clipboard:
#xclip -selection clipboard

#Get Kth line:
#sed -n 3p # K = 3

# cat the last run's log
#cat "$(ls -t | head -n1)"