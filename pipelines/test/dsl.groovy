pipelineJob('TestPipeline') {
    displayName('Test Pipeline')
    description('Test pipeline for DSL')

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
            scriptPath('pipelines/test/Jenkinsfile')
        }
    }
}
