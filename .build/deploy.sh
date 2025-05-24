# Script qui envoie le code sur le robot

# https://stackoverflow.com/questions/19331497/set-environment-variables-from-file-of-key-value-pairs
export $(cat .env.local | xargs)

env | grep DEPLOY

if [ -z "$DEPLOY_SERVER_IDENTITY_FILE_PATH" ]
then
    ssh $DEPLOY_SERVER_USER@$DEPLOY_SERVER_HOST "mkdir -p $DEPLOY_SERVER_DIR"
    rsync -avz --delete -e ssh ia config requirements.txt $DEPLOY_SERVER_USER@$DEPLOY_SERVER_HOST:$DEPLOY_SERVER_DIR
else
    ssh -i "$DEPLOY_SERVER_IDENTITY_FILE_PATH" $DEPLOY_SERVER_USER@$DEPLOY_SERVER_HOST "mkdir -p $DEPLOY_SERVER_DIR"
    rsync -avz --delete -e "ssh -i $DEPLOY_SERVER_IDENTITY_FILE_PATH" ia config requirements.txt $DEPLOY_SERVER_USER@$DEPLOY_SERVER_HOST:$DEPLOY_SERVER_DIR
fi