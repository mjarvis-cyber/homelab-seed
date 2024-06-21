job('MyPipelineJob') {
    displayName('Test pipeline for DSL')
    description('Test pipeline for DSL')

    scm {
        git {
            remote {
                url('https://github.com/your/repository.git')
            }
            branch('master')
        }
    }


    triggers {
        cron('H * * * *')
    }

    steps {
        stage('Test step') {
            steps {
                script {
                    cleanWs()
                    sh 'echo hello world!'
                }
            }
        }
    }
}
