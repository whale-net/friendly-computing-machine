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

k8s_yaml([
    'charts/friendly-computing-machine/dev/otel_collector/config.yaml',
    'charts/friendly-computing-machine/dev/otel_collector/deployment.yaml',
    'charts/friendly-computing-machine/dev/otel_collector/service.yaml'
])

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
            'image.tag=dev',
            'env.slack.botToken={}'.format(os.getenv('SLACK_BOT_TOKEN')),
            'env.slack.appToken={}'.format(os.getenv('SLACK_APP_TOKEN')),
            'env.google.api_key={}'.format(os.getenv('GOOGLE_API_KEY')),
            'env.db.url={}'.format(os.getenv('DATABASE_URL')),
            'env.otelCollector.logs.endpoint=http://otel-collector.{}.svc.cluster.local:4317'.format(namespace),
            'env.otelCollector.traces.endpoint=http://otel-collector.{}.svc.cluster.local:4317'.format(namespace),
            'namespace={}'.format(namespace),
            'deployment.skip_migration_check=false'
        ]
    )
)
