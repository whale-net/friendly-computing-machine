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

load('ext://helm_resource', 'helm_resource', 'helm_repo')
helm_repo('dev-util', 'https://whale-net.github.io/dev-util')
# setup postgres
helm_resource('otelcollector-dev', 'dev-util/otelcollector-dev', resource_deps=['dev-util'],
    flags=['--set=namespace={}'.format(namespace)]
)
# no need to publicly expose otel collector
#k8s_resource(workload='otelcollector-dev', port_forwards='4317:4317')

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
            'env.manman.host={}'.format(os.getenv('MANMAN_HOST_URL')),
            'env.rabbitmq.host={}'.format(os.getenv('FCM_RABBITMQ_HOST', 'localhost')),
            'env.rabbitmq.port={}'.format(os.getenv('FCM_RABBITMQ_PORT', '5672')),
            'env.rabbitmq.user={}'.format(os.getenv('FCM_RABBITMQ_USER', 'guest')),
            'env.rabbitmq.password={}'.format(os.getenv('FCM_RABBITMQ_PASSWORD', 'guest')),
            'env.rabbitmq.enableSsl={}'.format(os.getenv('FCM_RABBITMQ_ENABLE_SSL', 'false')),
            'env.otelCollector.logs.endpoint=http://otel-collector.{}.svc.cluster.local:4317'.format(namespace),
            'env.otelCollector.traces.endpoint=http://otel-collector.{}.svc.cluster.local:4317'.format(namespace),
            'namespace={}'.format(namespace),
            'deployment.skip_migration_check=false',
            'deployment.health.enabled=false',
            'env.temporal.host=http://host.docker.internal:7233'
        ]
    )
)
