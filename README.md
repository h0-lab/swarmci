Swarm CI
========

SwarmCI in it's currently stage (super alpha) is an CI/CD extension. You can extend your existing build system (jenkins, bamboo, teamcity), with parallel, distributing, isolated build tasks by leveraging a Docker Swarm.

## Inspiration
This project inspired me because of the problems I've faced with conventional CI/CD platforms like Jenkins, Bamboo, Teamcity.

### Local platforms (Bamboo, Teamcity and Jenkins, ...)

1. Agents have no isolation from the build tasks, sometimes causing hard to reproduce issues involving subprocesses and limitations of the build agent.
2. Agent VM/Containers need to be customized with differing capabilities (SDKs, versions, libraries, resources like cpu/mem, etc). 
    * This requires either an Ops team to maintain the permutations of build capabilities, or
    * Requires each build to install it's dependencies at build time, resulting in longer build times
3. Build-Agent binding, required when builds need specific things pre-installed, is wasteful as you must wait for an idle agent that meets the build requirements before the build will run.
3. An agent is no longer "untouched" after the first build it runs. State changes between builds can cause unexpected failures or worse, false-successes (unless the machine was re-provisioned after every build, not an easy or cheap thing to do).
4. Adding parallelism to your build pipeline requires licensing of additional agents, which can be very expensive (in addition to the hardware).
5. Build agents are often underutilized, either idle, or running builds with low system requirements.

### Online Platforms (TravisCI, CircleCI, CodeShip, ...)

1. Base images/os availability is limited. With SwarmCI, you can choose your base image, pre-loaded with whatever dependencies you need, resulting in fewer setup/dependency steps, in turn making your builds faster and simpler.
2. Being assigned arbitrary defaults or limited system resources can cause pipeline bottlenecks. In addition, it might be hard to realize you have a bottleneck or are being throttled.d visibility, offering no insight into build bottlenecks or transient failures.
3. Cost can still be significantly reduced, as an example, by putting your Docker Swarm on AWS Spot Instances.

## What it does
You can use SwarmCI to extend an existing CI system (Bamboo, TeamCity, Jenkins, etc) with a few steps.

1. Setup a Docker Swarm.
2. Converting existing build tasks, stages, and jobs to a single `.swarmci` file.
3. Configure a single task in your build to run a single command to delegate work to your Docker Swarm:

`python -m swarmci`

## Getting Started

### Composing a `.swarmci` file

#### Build Layers

A `.swarmci` file consists of several layers.

* `Stages` are run sequentially (identified with unique names). Subsequent stages only start if all jobs from a prior stage complete successfully.
* `Jobs` run in parallel (identified with unique names). Each job consists of one or more tasks, and various bits of meta data.
* `Tasks` are run sequentially within a job on a common container.

Each job consists of several pieces of information:

* `image(s)` **(required)**: the image to be used for all tasks within this job. This image should be on an available registry for the swarm to pull from (or be built using the `build` task). It should not have an entrypoint, as we'll want to execute an infinite sleep shell command so that it _does not exit_, because all tasks will run on this container, and SwarmCI expects to be able to launch the container, leave it running, and exec tasks on the running container. ~~This can be either a string or a list. When in list form, this job will be converted to a [job matrix](#job-matrix).~~
* `env` _(optional)_: environment variables to be made available for `tasks`, `after_failure`, and `finally_task`. This can be dictionary or a list of dictionaries. ~~When in list form, this job will be converted to a [job matrix](#job-matrix).~~
* `build` _(optional)_: Similar to the [docker compose build](https://docs.docker.com/compose/compose-file/#build). The SwarmCI agent can build and run the docker image locally before running tasks. The name of the built image will be that of the `image` key within the job.
* `task(s)` **(required)**: This can be either a string or a list. If any task in the list fails, subsequent tasks will not be run, however, `after_failure` and `finally` will run if defined.
* `after_failure` _(optional)_: this runs if any task task fails. This can be either a string or a list.
* `finally_task` _(optional)_: this runs regardless of result of prior tasks. This can be either a string or a list.

Full Example:

```yaml
stages:
  - my_stage:
    - name: my_job
      image: python:alpine
      env:
        say_something: hello from
      tasks:
        - /bin/sh -c 'echo "$say_something $HOSTNAME"'
        - /bin/sh -c 'echo "second task within my_job in $HOSTNAME"'
      after_failure: /bin/echo "this runs if any script task fails"
      finally_task: /bin/echo "this runs regardless of the result of the script tasks"
    - name: another_job
      image: python:alpine
      tasks:
        - /bin/sh -c 'echo "another_job says hello from $HOSTNAME"'
  - second_stage:
    - name: default_job_in_second_stage
      image: python:alpine
      tasks:
        - /bin/sh -c 'echo "look my, second stage job running in $HOSTNAME"'

```

#### <a name="job-matrix"></a>TODO: Job Matrix

When a job is converted to a job-matrix, you get all possible combinations of `image` and `env` variables. Here is an example job matrix that expands to 6 individual (3 \* 2) jobs.

```yaml
bar-job:
  image:
    - my-ci-python:2.7
    - my-ci-python:3.2
    - my-ci-python:3.5
  env:
    - db: mysql
      foo: v1
    - db: mysql
      foo: v2
  # note: all tasks will run for each expanded job instance
```

## Demo

```
vagrant up
vagrant ssh manager
/opt/swarmci/run-demo.sh
```

## Running Tests

```
python3.5 runtox.py -e linting,py35,py36
```

or using docker

```
docker build -t swarmci . 
docker build -f Dockerfile.test -t swarmci:test .        
docker run -it swarmci:test
```

## RoadMap

### Immediate

- Improved CLI
  - The output is very hard to read with jobs run in parallel
  - The output in general needs some love.
     - Color output (https://github.com/jkbrzt/httpie#colors-and-formatting)
- User Interface
- API
- Data Persistence

### Later

- Caching (like https://docs.travis-ci.com/user/caching/)
- Docker Builds
- Docker Compose
- Docker Push
- Secrets Management (For private repositories)
- Automatic Git Cloning (requires the secrets management above)
- Job Matrix (like https://docs.travis-ci.com/user/customizing-the-build/#Build-Matrix)
- Timeouts
- Manually Started Stages/Jobs
- Build Diff (Compare build output, commits, etc) *This is a feature I haven't seen much anywhere
- Automatic test parallelism (https://circleci.com/docs/test-metadata/)
