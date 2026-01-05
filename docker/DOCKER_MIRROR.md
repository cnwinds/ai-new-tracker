# Docker 镜像加速配置指南

本项目使用渡渡鸟（[docker.aityp.com](https://docker.aityp.com)）提供的华为云镜像加速服务。

## 当前配置

项目的 Dockerfile 已经直接使用渡渡鸟提供的华为云镜像源：

- **后端**：`swr.cn-north-4.myhuaweicloud.com/ddn-k8s/docker.io/python:3.11-slim`
- **前端构建**：`swr.cn-north-4.myhuaweicloud.com/ddn-k8s/docker.io/node:18-alpine`
- **前端运行**：`swr.cn-north-4.myhuaweicloud.com/ddn-k8s/docker.io/nginx:alpine`

## 查询其他镜像

如果需要使用其他 Docker 镜像，可以访问 [https://docker.aityp.com](https://docker.aityp.com) 查询对应的国内加速地址。

在网站上搜索镜像名称（如 `python:3.11-slim`），即可获取对应的华为云镜像地址，格式为：
```
swr.cn-north-4.myhuaweicloud.com/ddn-k8s/docker.io/镜像名
```

## 验证镜像拉取

```bash
# 测试拉取镜像
docker pull swr.cn-north-4.myhuaweicloud.com/ddn-k8s/docker.io/python:3.11-slim

# 查看镜像信息
docker images | grep python
```

## 常见问题

### 镜像拉取失败

如果遇到镜像拉取失败：
1. 检查网络连接
2. 访问 [docker.aityp.com](https://docker.aityp.com) 确认镜像是否已同步
3. 某些镜像可能需要等待同步（通常 1 小时内完成）

### 企业内网环境

- 需要配置代理服务器
- 或使用内网私有镜像仓库
