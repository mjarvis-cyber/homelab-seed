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
            scriptPath('pipelines/template-creator/jenkinsfile.groovy')
        }
    }
    definition {
        cps {
            script("""
                pipeline {
                    agent {
                        dockerfile {
                            filename 'Dockerfile'
                        }
                    }
                    stages {
                        stage('Checkout') {
                            steps {
                                checkout([$class: 'GitSCM',
                                    branches: [[name: '*/master']],
                                    doGenerateSubmoduleConfigurations: false,
                                    extensions: [],
                                    userRemoteConfigs: [[url: 'https://github.com/OrangeSquirter/homelab-seed.git']]
                                ])
                            }
                        }
                        stage('Build Templates') {
                            steps {
                                script {
                                    dir('pipelines/template-creator') {
                                        sh 'python template-creator.py'
                                    }
                                }
                            }
                        }
                    }
                }""")
        }
    }
}
