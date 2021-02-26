import csv
import argparse
import datetime
import os

from collections import defaultdict
from pathlib import Path


def load_records(containing_dir):
    dir = Path(containing_dir)
    metadata_file = [f for f in dir.iterdir() if f.suffix == '.csv']
    if metadata_file:
        metadata_file = metadata_file[0]
    else:
        raise ValueError(f'No metadatafile found in {dir}')

    with metadata_file.open('r', encoding='utf-8') as ip:
        metadata = list(csv.DictReader(ip))

    text_root = dir / 'plaintext'
    for md in metadata:
        text = text_root / md['Filename']
        md['Article'] = text.read_text(encoding='utf-8')

    return metadata


def collect_articles(root):
    root = Path(root)
    dirs = [f for f in root.iterdir()
            if f.is_dir() and f.stem != 'search_records']
    return [a for d in dirs for a in load_records(d)]


def ymd_to_mdy(d_str):
    try:
        return datetime.datetime.strptime(
            d_str,
            '%Y-%m-%d'
        ).strftime('%m/%d/%Y')
    except (ValueError):
        return d_str


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        'root_directory',
        type=str,
        help='The root input directory. This should be the directory '
             'containing the "search_records" folder.'
    )
    parser.add_argument(
        'output_directory',
        type=str,
        help='The output directory.'
    )
    return parser.parse_args()


if __name__ == '__main__':
    args = parse_args()
    articles = collect_articles(args.root_directory)

    days = defaultdict(list)
    for a in articles:

        text = a['Article']
        pub = a['Publication']
        title = a['Title']
        author = a['Author']
        date = a['Date']
        mdy_date = ymd_to_mdy(date)
        metadata = ('Title: {}'.format(title),
                    'Description: {}'.format(author),
                    'Channel: {}'.format(pub),
                    'Recorded On: {}'.format(mdy_date),
                    'Original Air Date: {}'.format(mdy_date))
        metadata = '\n'.join(metadata)
        outdata = '=========='.join((metadata, text))
        outdata = outdata.replace('\r', '\n').encode('utf-8')
        days[date].append(outdata)

    head = b'\xc3\xaf\xc2\xbb\xc2\xbf'
    sep = b'\n' + head
    for d in days:
        days[d][0] = head + days[d][0]
        days[d] = sep.join(days[d])

    for d in days:
        fn = d + '-Combined.txt'
        with open(os.path.join(args.output_directory, fn), 'wb') as out:
            out.write(days[d])
            out.write('\n'.encode('utf-8'))
