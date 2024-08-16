
pipelineJob('jenkins-agent-builder') {
    displayName('Jenkins Agent Builder')
    description('Deploy Jenkins Agents')

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
            scriptPath('pipelines/jenkins-agent-builder/Jenkinsfile')
        }
    }
}
