
DEPENDENCIES
------------

The following PyPI packages are required:
	conllu
	pyyaml



USAGE
-----

As command line script:

	conllu2yaml.py <conllu-file> [<conllu-file> ...]


From python:

	import conllu2yaml


	# A single specified input and output file handle
	in = open('input-file-path.conllu', 'r', encoding='utf-8')
	out = open('output-file-path.yaml', 'w', encoding='utf-8')
	conllu2yaml.convert(in, out)
	in.close()
	out.close()


	# A single specified input and output filename
	conllu2yaml.convert_file('input-file-path.conllu', 'output-file-path.yaml')


	# A list of conllu filenames:
	conllu2yaml.convert_all_files(['file1.conllu', 'file2.conllu', 'file3.conllu'])



