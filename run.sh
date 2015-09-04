if [ "$SUBPROC_TYPE" == "python" ]; then
    gunicorn api.server:app --log-file=-
else
    node web.js
fi
