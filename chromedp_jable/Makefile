PROJECTNAME=$(shell basename "$(PWD)")
# Binary package name for release
BINARY=chromedp_jable

# Go related variables.
GOBASE=$(shell pwd)

GOPATH :=$(shell echo ${GOPATH})
# Go binary store place.
GOBIN=$(GOBASE)/bin
GORELEASE=$(GOBASE)/release
GOFILES=$(wildcard *.go)
GOBUILD_RACE=go build -race -o 
GOBUILD=go build -o

# Redirect error output to a file, so we can show it in development mode.
STDERR=/tmp/.$(PROJECTNAME)-stderr.txt

# PID file will keep the process id of the server
PID=/tmp/.$(PROJECTNAME).pid

# Make is verbose in Linux. Make it silent.
MAKEFLAGS += --silent


.PHONY: help
all: help
help: Makefile
	@echo
	@echo " Choose a command run in "$(PROJECTNAME)":"
	@echo
	@sed -n 's/^##//p' $< | column -t -s ':' |  sed -e 's/^/ /'
	@echo


go-compile: clean-bin go-get go-build

go-build:
	@echo "  >  Building binary..."
	@GOOS=linux GOARCH=amd64 $(GOBUILD) $(GOBIN)/$(PROJECTNAME)
	@echo "  >  Building done."

go-generate:
	@echo "  >  Generating dependency files..."
	@GOPATH=$(GOPATH) GOBIN=$(GOBIN) go generate $(generate)

go-get:
	@echo "  >  Checking if there is any missing dependencies..."
	#@GOPATH=$(GOPATH) GOBIN=$(GOBIN) go get $(get)

go-install:
	@GOPATH=$(GOPATH) GOBIN=$(GOBIN) go install $(GOFILES)

clean-bin:
	@echo "  >  Cleaning build cache..."
	@-rm $(GOBIN)/* 2> /dev/null


clean-release:
	@echo "  >  Cleaning release file..."
	@-rm $(GORELEASE)/* 2> /dev/null

## install: Install missing dependencies. Runs `go get` internally. e.g; make install get=github.com/foo/bar
install: go-get

## compile: Compile the x86_64 Linux binary without race check.
compile:
	@-touch $(STDERR)
	@-rm $(STDERR)
	@-$(MAKE) go-compile 2> $(STDERR)
	@cat $(STDERR) | sed -e '1s/.*/\nError:\n/'  | sed 's/make\[.*/ /' | sed "/^/s/^/     /" 1>&2


## clean: Clean build files and release file.
clean: clean-bin clean-release


## release: Release arm64 and x86_64 linux binary package.
release: clean-release
	@echo "  >  Creating release file..."
	@CGO_ENABLED=0 GOOS=linux GOARCH=arm64 $(GOBUILD) $(GORELEASE)/$(BINARY)_arm64_liunx
	@CGO_ENABLED=0 GOOS=linux GOARCH=amd64 $(GOBUILD) $(GORELEASE)/$(BINARY)_x86_64_linux
	@CGO_ENABLED=0 GOOS=darwin GOARCH=arm64 $(GOBUILD) $(GORELEASE)/$(BINARY)_arm64_darwin
	@CGO_ENABLED=0 GOOS=darwin GOARCH=amd64 $(GOBUILD) $(GORELEASE)/$(BINARY)_x86_64_darwin
	@CGO_ENABLED=0 GOOS=windows GOARCH=arm64 $(GOBUILD) $(GORELEASE)/$(BINARY)_arm64_windows
	@CGO_ENABLED=0 GOOS=windows GOARCH=amd64 $(GOBUILD) $(GORELEASE)/$(BINARY)_x86_64_windows