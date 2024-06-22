pipeline {
    agent {
        dockerfile {
            filename 'pipelines/template-creator/Dockerfile'
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
}
