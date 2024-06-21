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
                    userRemoteConfigs: [[url: 'https://your.git.repo.url']]
                ])
            }
        }
        stage('Build Templates') {
            steps {
                script {
                    dir('pipelines/template-creator'){
                        sh 'python template-creator.py'
                    }
                }
            }
        }
    }
}
