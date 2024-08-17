pipelineJob('box-builder') {
    displayName('Box Terminator')
    description('Terminate a VM')

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
            scriptPath('pipelines/box-terminator/Jenkinsfile')
        }
    }
}
