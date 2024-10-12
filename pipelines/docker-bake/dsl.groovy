pipelineJob('docker-bake') {
    displayName('Docker Bake')
    description('Docker bake and push to docker registry')

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
            scriptPath('pipelines/docker-bake/Jenkinsfile')
        }
    }
}
