import click


@click.command()
@click.argument('subcommand', default='help')
def main(subcommand):
    if subcommand == 'help':
        print(' clear: clear all cache')
    if subcommand == 'clear':
        pass


if __name__ == '__main__':
    main()
