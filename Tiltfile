load('ext://namespace', 'namespace_create')
# appending '-dev' just in case this is ever ran from prod cluster
namespace = 'fcm-dev'
namespace_create(namespace)

load('ext://dotenv', 'dotenv')
# load env vars from .env
dotenv()

docker_build(
    'fcm',
    context='.'
)

# create fcm app
k8s_yaml(
    helm(
        'charts/friendly-computing-machine',
        name='fcm',
        namespace=namespace,
        # using set instead of values, for now? for ever?
        #values=['path/to'],
        set=[
            'image.name=fcm',
            'env.slack.botToken={}'.format(os.getenv('SLACK_BOT_TOKEN')),
            'env.slack.appToken={}'.format(os.getenv('SLACK_APP_TOKEN')),
            'env.db.url={}'.format(os.getenv('DATABASE_URL')),
            'namespace={}'.format(namespace),
            'deployment.skip_migration_check=false'
        ]
    )
)
