.PHONY: README

README:
	pandoc --from=markdown --to=rst --output=README README.md


