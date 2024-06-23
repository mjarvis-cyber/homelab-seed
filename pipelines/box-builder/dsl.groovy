pipelineJob('box-builder') {
    displayName('Box Builder')
    description('Deploy')

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
            scriptPath('pipelines/box-builder/Jenkinsfile')
        }
    }
}
