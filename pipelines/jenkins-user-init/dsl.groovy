pipelineJob('jenkins-user-init') {
    displayName('Jenkins User Init')
    description('Initialize jenkins user, only run once.')

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
            scriptPath('pipelines/jenkins-user-init/Jenkinsfile')
        }
    }
}
