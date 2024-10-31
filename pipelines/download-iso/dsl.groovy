
pipelineJob('download-iso') {
    displayName('Image Downloader')
    description('Downloads an iso image to a proxmox server')

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
            scriptPath('pipelines/download-iso/Jenkinsfile')
        }
    }
}
