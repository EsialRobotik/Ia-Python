# Script qui envoie le code sur le robot

# https://stackoverflow.com/questions/19331497/set-environment-variables-from-file-of-key-value-pairs
export $(cat .env.local | xargs)

env | grep DEPLOY

if [ -z "$DEPLOY_SERVER_IDENTITY_FILE_PATH" ]
then
    scp -r ia config requirements.txt logs $DEPLOY_SERVER_USER@$DEPLOY_SERVER_HOST:$DEPLOY_SERVER_DIR
else
    scp -i "$DEPLOY_SERVER_IDENTITY_FILE_PATH" -r ia config requirements.txt logs $DEPLOY_SERVER_USER@$DEPLOY_SERVER_HOST:$DEPLOY_SERVER_DIR
fi