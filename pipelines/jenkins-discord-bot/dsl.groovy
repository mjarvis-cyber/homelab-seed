pipelineJob('Discord Bot') {
    displayName('Discord Bot')
    description('Jenkins Discord Bot')

    definition {
        cpsScm {
            scm {
                git {
                    remote {
                        url('git@github.com:OrangeSquirter/jenkins-discord-bot.git')
                        credentials('ssh-key')
                    }
                    branch('master')
                }
            }
            scriptPath('pipelines/test/Jenkinsfile')
        }
    }
}
