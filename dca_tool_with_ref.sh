#!/bin/bash
L_REPERTOIRE="${PWD}/$(dirname $0)"
L_PYTHON_ENV="${L_REPERTOIRE}/env/bin/activate"
L_PYTHON_SCRIPT="${L_REPERTOIRE}/dca_with_ref.py"

if [ -f "${L_PYTHON_ENV}" ]
then
    L_DATE=$(date +'%Y_%m_%d')
    L_LOG_FILE="${L_REPERTOIRE}/log/LOG_DCA_${L_DATE}_${2}"
    source "${L_PYTHON_ENV}"
    python "${L_PYTHON_SCRIPT}" "$1" "$2" "$3" &> $L_LOG_FILE
    L_RC=$?
    if [ "${L_RC}" -eq 42 ]
    then
        cat "${L_LOG_FILE}" 
        rm "${L_LOG_FILE}"
    else
        L_RESULT=$(cat "${L_LOG_FILE}"| grep ERROR | wc -l)
        cat "${L_LOG_FILE}"
        if [ "${L_RESULT}" -eq 0 ]
        then
            cat "${L_LOG_FILE}" | mail -s "SUCCESS Log: ${L_DATE}" sudoweezy@gmail.com
            rm "${L_LOG_FILE}"
        else
            cat "${L_LOG_FILE}" | mail -s "ERROR Log: ${L_DATE}" sudoweezy@gmail.com
        fi
    fi
    deactivate
else
    echo "$L_PYTHON_ENV does not exist"
fi
