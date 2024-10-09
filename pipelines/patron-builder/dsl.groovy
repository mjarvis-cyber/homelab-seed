
pipelineJob('patron-builder') {
    displayName('Patron Builder')
    description('Create Patron Environment')

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
            scriptPath('pipelines/patron-builder/Jenkinsfile')
        }
    }
}
