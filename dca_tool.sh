L_REPERTOIRE="${PWD}/$(dirname $0)"
L_PYTHON_ENV="${L_REPERTOIRE}/env/bin/activate"
L_PYTHON_SCRIPT="${L_REPERTOIRE}/LiveCryptocom/dca.py"

echo "Repertoire $L_REPERTOIRE" 
if [ -f "${L_PYTHON_ENV}" ]
then
	L_DATE=$(date +'%Y_%m_%d')
	L_LOG_FILE="${L_REPERTOIRE}/log/LOG_DCA_${L_DATE}"
	source "${L_PYTHON_ENV}"
	python "${L_PYTHON_SCRIPT}" "$1" "$2" > $L_LOG_FILE
	L_RESULT=$(cat $L_LOG_FILE| grep ERROR | wc -l)
	if [ "${L_RESULT}" -eq 0 ]
	then
		rm $L_LOG_FILE
	else
		cat $L_LOG_FILE | mail -s "Log: ${L_DATE}" sudoweezy@gmail.com
	fi

	deactivate
else
	echo "$L_PYTHON_ENV does not exist"
fi