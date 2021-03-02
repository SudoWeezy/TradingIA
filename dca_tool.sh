L_PYTHON_ENV="${PWD}/env/bin/activate"
L_PYTHON_SCRIPT="${PWD}/LiveCryptocom/dca.py"
if [ -f "${L_PYTHON_ENV}" ]
then
	L_DATE=$(date +'%Y_%m_%d')
	L_LOG_FILE="log/LOG_DCA_${L_DATE}"
	source "${L_PYTHON_ENV}"
	python "${L_PYTHON_SCRIPT}" "reference=USDT" "withdraw=NO" > $L_LOG_FILE
	L_RESULT=$(cat $L_LOG_FILE| grep ERROR | wc -l)
	if [ "${L_RESULT}" -eq 0 ]
	then
		rm $L_LOG_FILE
	fi

	deactivate
else
	echo "$L_PYTHON_ENV does not exist"
fi