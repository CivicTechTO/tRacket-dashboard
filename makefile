.PHONY: app


#################
### VARIABLES ###
#################

API_TOKEN=`grep 'API_TOKEN' config.env | sed 's/^.*=//'`
HEROKU_EMAIL=`grep 'HEROKU_EMAIL' config.env | sed 's/^.*=//'`
HEROKU_API_KEY=`grep 'HEROKU_API_KEY' config.env | sed 's/^.*=//'`
APP_PORT = 8501
CONTAINER_NAME = noise-dashboard
PROD_IMAGE_NAME = noise-dashboard
DEV_IMAGE_NAME = $(PROD_IMAGE_NAME)-dev
HEROKU_APP_NAME = noise-dashboard

api_token:
	echo $(API_TOKEN)

#############
### HOOKS ###
#############


install-pre-commit:
	pip install pre-commit

setup-pre-commit:
	pre-commit install


##############
### HEROKU ###
##############

heroku_login:
	echo "machine api.heroku.com" > ~/.netrc;\
	echo "	login $(HEROKU_EMAIL)" >> ~/.netrc;\
	echo "	password $(HEROKU_API_KEY)" >> ~/.netrc;\
	echo "machine git.heroku.com" >> ~/.netrc;\
	echo "	login $(HEROKU_EMAIL)" >> ~/.netrc;\
	echo "	password $(HEROKU_API_KEY)" >> ~/.netrc;\
	docker login --username=$(HEROKU_EMAIL) --password=$(HEROKU_API_KEY) registry.heroku.com;

	

heroku_push:
	docker tag $(PROD_IMAGE_NAME) registry.heroku.com/$(HEROKU_APP_NAME)/web
	docker push registry.heroku.com/$(HEROKU_APP_NAME)/web

heroku_release:
	heroku container:release web -a $(HEROKU_APP_NAME)

##############
### DOCKER ###
##############

build: dev_build prod_build

### RUN ###


dev_container: docker_clean
	docker run -it\
		-v "$(PWD)":/project\
		-p $(APP_PORT):$(APP_PORT)\
		-p 8888:8888\
		-w /project\
		-e PORT=$(APP_PORT)\
		--name $(CONTAINER_NAME)\
		$(DEV_IMAGE_NAME)

prod_container: docker_clean
	docker run -d\
		-p $(APP_PORT):$(APP_PORT)\
		-e PORT=$(APP_PORT)\
		--name $(CONTAINER_NAME)\
		$(PROD_IMAGE_NAME)

### BUILD ###

prod_build:
	docker build --build-arg TOKEN=$(API_TOKEN) --no-cache --target prod-builder -t $(PROD_IMAGE_NAME) .

dev_build:
	docker build --build-arg TOKEN=$(API_TOKEN) --target dev-builder -t $(DEV_IMAGE_NAME) .

### COMPOSE ###

# dev_compose:
# 	docker compose -f docker-compose.dev.yml up -d --build

# prod_compose:
# 	docker compose -f docker-compose.yml up -d --build

### CLEANUP ###

docker_clean:
	docker stop $(CONTAINER_NAME) || true && docker container rm $(CONTAINER_NAME) || true

###############
### TESTING ###
###############

test:
	pytest .


###########
### PIP ###
###########

pip_export:
	pip freeze > requirements.txt

################
### RUN APPs ###
################

notebook:
	jupyter notebook --ip 0.0.0.0 --no-browser --allow-root

app:
	(cd /project/app; gunicorn --bind 0.0.0.0:$(APP_PORT) app:server)

debug:
	(cd /project/app; python app.py)


#############
### Utils ###
#############

count:
	wc -l **/*.py makefile Dockerfile README.md