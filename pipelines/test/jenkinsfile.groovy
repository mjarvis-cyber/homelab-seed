pipeline {

    agent {
        label 'controller'
    }


    stages {
        stage('Init seed') {
            steps {
                script {
                    cleanWs()
                    sh "echo hello world!"
                }
            }
        }
    }
}
