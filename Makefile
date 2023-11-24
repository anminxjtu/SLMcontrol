.PHONY: filelist count

filelist:
	@git ls-files|xargs wc -lw

count:
	@git log --author="b034" --pretty=tformat: --numstat
	@git ls-files|xargs wc -lw

commit:
	@git log --oneline | wc -l

