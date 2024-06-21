pipelineJob('TestPipeline') {
    displayName('Test pipeline for DSL')
    description('Test pipeline for DSL')

    definition {
        cpsScm {
            scm {
                git {
                    remote {
                        url('https://github.com/OrangeSquirter/homelab-seed.git')
                    }
                    branch('master')
                }
            }
            scriptPath('pipelines/test/jenkinsfile.groovy')
        }
    }

    triggers {
        cron('H * * * *')
    }

    parameters {
        stringParam('PARAM_NAME', 'default_value', 'Description of parameter')
    }

    definition {
        cps {
            script("""
                pipeline {
                    agent any
                    stages {
                        stage('Build') {
                            steps {
                                script {
                                    cleanWs()
                                    sh 'echo hello world!'
                                }
                            }
                        }
                        // Add more stages as needed
                    }
                }
            """)
        }
    }
}
