#!/bin/bash
i=0
o=0
_jq () { 
	echo ${row} | base64 -d | jq -r ${1}
}
echo "## Exporting from Contentful ##"
read -p "Pull export? [y/N]: " pull
if [[ "$pull" == "y" ]]
then
	contentful space export --environment-id german-rollout-staging --query-entries 'content_type=agentPortalTranslation' --content-only --content-file contentful-export.json
fi
rm -fr output && mkdir -p output
tdone=$(jq '.entries[] | .fields.value.de' contentful-export.json | grep -v null | wc -l ) 
ttodo=$( jq '.entries[] | .fields.value.de' contentful-export.json | grep null | wc -l )
ttotal=$( echo $tdone+$ttodo | bc )
echo "## $tdone übersetzt und noch $ttodo zu erledigen von insgesamt $ttotal. Weiter mit [ENTER] ##"
read
for row in $( cat contentful-export.json | jq '.entries[]  | @base64' | tr -d "\"" );
do
	let i=i+1
	de=$( _jq '.fields.value.de' )
	if [ "$de" == "null" ]
	then
		clear
		full=$( _jq '.' )
		id=$( _jq '.sys.id' )
		key=$( _jq '.fields.key.en' )
		en=$( _jq '.fields.value.en' )
		redo=y
		while [[ "$redo" == "y" ]]; do

			echo "## Missing translation found ##"
			let o=o+1
			echo $i $o $id $key
			echo EN: $en
			read -p "DE: " de
			echo
			echo "## New translation ##"
			echo $id $key
			echo EN: $en
			echo DE: $de
			echo
			read -p "Redo? [y/N]: " redo
		done
		deadd='{"fields":{"value":{"de":"'$de'"}}}'
		echo $full > t1
		echo $deadd > t2
		full=$( jq -s '.[0] * .[1]' t1 t2 ) 
		echo $full> output/${id}.json
		read -p "Continue [Y/n]: " continue
		if [[ "$continue" == "n" ]]
		then
			break
		fi
	fi
done
echo 
echo "## Building import file ##"
jq . output/* -sS -c > tmp.json
cat head tmp.json foot | jq . -c > contentful-import.json
echo "## Importing to Contentful ##"
contentful space import --environment-id german-rollout-staging --content-file `pwd`/contentful-import.json
