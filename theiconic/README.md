# Superset

### New Features!

  - Email scheduling for Dashboard
  - Email scheduling for Chart

### Installation


Run Superset in your local environement!

Download Superset in your local machine by running following command
```
git clone https://github.com/theiconic/superset superset
```

Let go inside superset directory
```
cd superset
```
Create a new .env file from .env.sample file. New file will be used to set all required environement variables!
```
cp .env.sample .env
```
Move .env file to new location. This file will be used by docker-compose to load all variables into environment.
```
mv .env .cicd/docker/
```

**Nice work!**

Now lets build docker image for Superset. We have Makefile where you find all available commands related to building image, running and stopping Superset!

Run following command to see what we have in Makefile
```
cat Makefile
```

Its time to build docker image for Superset by running following command.
```
make superset-build
```
Optinally you can use `SUPERSET_BRANCH={branch_name}` along with previous command. When branch name is provided then code will be pulled from that branch of [incubator-superset](https://github.com/theiconic/incubator-superset) to build Superset docker
```
make superset-build SUPERSET_BRANCH=my-test-branch
```

Building image would take some. Once building process done you can run following docker command to see image.
```
docker images | grep superset
```
**Nice work again! Lets take sip of coffee**

Now we need to create admin user which we will use to access Superset(We will run Superset in next step).
```
make superset-create-admin
```
After running command you will be asked to provide `username`, `firstname`, `lastname`, `email` and `password`.

Lets run Superset by running following command & then we can access it by clicking [http://localhost:8088](http://localhost:8088)
```
make superset-up
```

Stop superset by running following command or Pressing `control + c` command
```
make superset-down
```

### Have idea to add more features in Superset?
Repo: [incubator-superset](https://github.com/theiconic/incubator-superset)
Create a new branch from master then work on that branch to more features then open a PR.


### Troubleshooting

If your superset application is not going up try to check the containers logs using docker-compose logs -f. It will show if
any dependent coontainer is dying due to bad configuration.

