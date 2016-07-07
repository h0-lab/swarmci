import pytest
import mock
import swarmci.agent as build_agent
from docker import Client
from assertpy import assert_that
from stage import Stage
from job import Job
from tests.conftest import example_yaml_path


def test_create_stages_given_yaml_expect_stage_objects_returned():
    """Convert yaml dict to Stages object"""
    stages = build_agent.create_stages(example_yaml_path)

    assert_that(stages).is_type_of(list)
    assert_that(stages).is_length(2)
    assert_that(stages[0]).is_type_of(Stage)


def test_run_stages_given_failed_first_stage_expect_latter_stages_not_run():
    """stages should only run if all jobs in prior stage are successful"""
    first_stage_jobs = [Job(name='test_job', images='foo', tasks='foo')]
    second_stage_jobs = [Job(name='sec_job', images='foo', tasks='foo')]
    stages = [
        Stage(name='test_stage', jobs=first_stage_jobs),
        Stage(name='second_stage', jobs=second_stage_jobs)
    ]

    run_stage_mock = mock.Mock(return_value=False)

    build_agent.run_stages(stages, run_stage_mock)

    run_stage_mock.assert_called_once_with(first_stage_jobs)


def test_run_stage_given_multiple_jobs_expect_run_all():
    """Expect all jobs to be run within the stage."""
    jobs = [
        Job(name='test1', images='foo', tasks='foo'),
        Job(name='test2', images='foo', tasks='foo')
    ]
    stage = Stage(
        name='test_stage',
        jobs=jobs
    )

    run_job_mock = mock.Mock(return_value=False)

    build_agent.run_stage(stage, run_job_func=run_job_mock)

    expected_calls = [
        mock.call(jobs[0]),
        mock.call(jobs[1])]

    run_job_mock.assert_has_calls(expected_calls)


@pytest.mark.parametrize(argnames=['side_effect', 'expectation'], argvalues=[
    [[False, True], False],
    [[True, False], False],
    [[True, True], True]
])
def test_run_stage_given_variable_job_return_expect_stage_return_on_failed_jobs(side_effect,
                                                                                expectation):
    """If any job fails, the whole stage should fail"""
    jobs = [
        Job(name='test1', images='foo', tasks='foo'),
        Job(name='test2', images='foo', tasks='foo')
    ]

    stage = Stage(
        name='test_stage',
        jobs=jobs
    )

    run_job_mock = mock.Mock(side_effect=side_effect)

    result = build_agent.run_stage(stage, run_job_func=run_job_mock)

    assert_that(result, "because first job failed.").is_equal_to(expectation)
