pipelineJob('discord-bot') {
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
            scriptPath('Jenkinsfile')
        }
    }
}
