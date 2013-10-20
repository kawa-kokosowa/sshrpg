import ConfigParser


def ini(path):
    parsed_config = {}

    path = 'config/' + path + '.ini'

    with open(path) as f:
        config = ConfigParser.ConfigParser()
        config.readfp(f)

        for k,v in config._sections.items():
            if v.get('var'):
                del v['var']

            if v['__name__']:
                del v['__name__']

            parsed_config[k] = v

    return parsed_config

