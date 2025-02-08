# Script qui envoie le code sur le robot

# https://stackoverflow.com/questions/19331497/set-environment-variables-from-file-of-key-value-pairs
export $(cat .env.local | xargs)

env | grep DEPLOY

if [ -z "$DEPLOY_SERVER_IDENTITY_FILE_PATH" ]
then
    scp -r ia $DEPLOY_SERVER_USER@$DEPLOY_SERVER_HOST:$DEPLOY_SERVER_DIR
    scp -r config $DEPLOY_SERVER_USER@$DEPLOY_SERVER_HOST:$DEPLOY_SERVER_DIR
    scp -r requirements.txt $DEPLOY_SERVER_USER@$DEPLOY_SERVER_HOST:$DEPLOY_SERVER_DIR
else
    scp -i "$DEPLOY_SERVER_IDENTITY_FILE_PATH" -r ia $DEPLOY_SERVER_USER@$DEPLOY_SERVER_HOST:$DEPLOY_SERVER_DIR
    scp -i "$DEPLOY_SERVER_IDENTITY_FILE_PATH" -r config $DEPLOY_SERVER_USER@$DEPLOY_SERVER_HOST:$DEPLOY_SERVER_DIR
    scp -i "$DEPLOY_SERVER_IDENTITY_FILE_PATH" requirements.txt $DEPLOY_SERVER_USER@$DEPLOY_SERVER_HOST:$DEPLOY_SERVER_DIR
fi