import pandas as pd


def post_xdxr(app, file_name):
    p = app['config']['xdxr_file_path']
    f = p + file_name

    df = pd.read_csv(f)

    print(df)


if __name__ == '__main__':
    app = {}
    app['config'] = {'xdxr_file_path': '/u01/my/mystockdata/xdxr/'}
    post_xdxr(app, '601600.csv')
