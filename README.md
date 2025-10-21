
<h1 align="center">🪂 Moroccan Royal Armed Forces - Airborne Troops</h1>
<h2 align="center">Face Recognition & Access Control System</h2>

<p align="center">
  <br>
  <i>Secure biometric access control and personnel tracking system for the Moroccan Airborne Troops.
     Military-grade face recognition platform providing REST API for face recognition, verification, detection, and comprehensive security monitoring.
     Designed for military bases, secure facilities, and operational deployments with complete offline capability.
     </i>
  <br>
</p>

<p align="center">
  <strong>المملكة المغربية - القوات المسلحة الملكية - القوات المحمولة جواً</strong><br>
  <strong>Kingdom of Morocco - Royal Armed Forces - Airborne Troops</strong><br>
  <em>Secure Military System - Based on CompreFace Open Source Technology</em>
  <br>
</p>

<p align="center">
  <a href="#contributing">Contributing</a>
  ·
  <a href="https://github.com/exadel-inc/CompreFace/issues">Submit an Issue</a>
  ·
  <a href="https://exadel.com/news/tag/compreface/">Blog</a>
  ·
  <a href="https://gitter.im/CompreFace/community">Community chat</a>
  <br>
</p>

<p align="center">
  <a href="https://www.apache.org/licenses/LICENSE-2.0">
    <img src="https://img.shields.io/github/license/exadel-inc/CompreFace" alt="GitHub license" />
  </a>&nbsp;
  <a href="https://github.com/exadel-inc/CompreFace/graphs/contributors">
    <img src="https://img.shields.io/github/contributors/exadel-inc/CompreFace" alt="GitHub contributors" />
  </a>&nbsp;
</p>
<hr>

# Table Of Contents

  * [Overview](#overview)
  * [Screenshots](#screenshots)
  * [Video tutorials](#videos)
  * [News and updates](#news-and-updates)
  * [Features](#features)
  * [Functionalities](#functionalities)
  * [Getting Started with CompreFace](#getting-started-with-compreface)
  * [CompreFace SDKs](#compreface-sdks)
  * [Documentation](/docs)
    * [How to Use CompreFace](/docs/How-to-Use-CompreFace.md)
    * [Face Services and Plugins](/docs/Face-services-and-plugins.md)
    * [Rest API Description](/docs/Rest-API-description.md)
    * [Postman documentation and collection](https://documenter.getpostman.com/view/17578263/UUxzAnde)
    * [Face Recognition Similarity Threshold](/docs/Face-Recognition-Similarity-Threshold.md)
    * [Configuration](/docs/Configuration.md)
    * [Architecture and Scalability](/docs/Architecture-and-scalability.md)
    * [Custom Builds](/docs/Custom-builds.md)
    * [Face data migration](/docs/Face-data-migration.md)
    * [User Roles System](/docs/User-Roles-System.md)
    * [Face Mask Detection Plugin](/docs/Mask-detection-plugin.md)
    * [Kubernetes configuration](https://github.com/exadel-inc/compreface-kubernetes)
    * [Gathering Anonymous Statistics](/docs/Gathering-anonymous-statistics.md)
    * [Installation Options](/docs/Installation-options.md)
  * [Contributing](#contributing)
  * [License info](#license-info)

# Overview

The Moroccan Royal Armed Forces Airborne Troops Face Recognition System is a military-grade biometric access control platform built on open-source CompreFace technology and customized for secure military operations.

This system is designed for deployment in military bases, secure facilities, and operational environments where personnel identification and access control are critical. The platform operates completely offline for maximum security and can be deployed in air-gapped networks.

**Military Applications:**
- Base access control and perimeter security
- Personnel attendance and duty tracking
- Secure facility access management
- Operational deployment personnel tracking
- Unauthorized intruder detection and alerts
- Integration with existing military CCTV infrastructure

The system provides comprehensive REST API for face recognition, verification, detection, and advanced biometric analysis. Features include role-based access control allowing military commanders to manage security permissions across different units, battalions, and operational areas.

Optimized for Apple Silicon (M3 Max with MPS GPU acceleration) and deployed as containerized services with support for both CPU and GPU processing.
Built on military-grade encryption and state-of-the-art AI models (FaceNet, InsightFace) with integration support for Hikvision 8MP surveillance cameras.

# Screenshots

<p align="center">
<img src="https://github.com/exadel-inc/CompreFace/assets/3736126/7b86a96f-844b-4e4b-9456-c53f6e45f305" 
alt="compreface-recognition-page" width=390px style="padding: 0px 10px 0px 0px;">
<img src="https://github.com/exadel-inc/CompreFace/assets/3736126/51efb9d0-70cc-4902-bc3f-fd85de004b67" 
alt="compreface-dashboard-page" width="390px" style="padding: 0px 0px 0px 10px;">
</p>

<details>
  <summary> <b>More Screenshots</b> </summary>
  <!-- have to be followed by an empty line! -->

<p align="center">
<img src="https://github.com/exadel-inc/CompreFace/assets/3736126/3ae0ce68-588b-4370-8eaf-32668c96fa63"
alt="compreface-verification-page" width=390px style="padding: 0px 10px 0px 0px;">
<img src="https://github.com/exadel-inc/CompreFace/assets/3736126/9246702d-1c9b-4435-8098-89e0fb616b0d"
alt="compreface-detection-page" width="390px" style="padding: 0px 0px 0px 10px;">
</p>
<p align="center">
<img src="https://github.com/exadel-inc/CompreFace/assets/3736126/3a5787e6-9a85-4852-92dc-a82fe7ef8f7c" 
alt="compreface-services-page" width=390px style="padding: 0px 10px 0px 0px;">
<img src="https://github.com/exadel-inc/CompreFace/assets/3736126/e7fd0258-2643-4cec-809d-988502eb857f" 
alt="compreface-wizzard-page" width="390px" style="padding: 0px 0px 0px 10px;">
</p>

</details>

# Videos

<p align="center">
<a target="_blank" href="https://www.youtube.com/watch?v=LS4sVTnI-gI">
     <img src="https://user-images.githubusercontent.com/3736126/241272669-8609463b-8b22-4ae7-bf21-36761f00734b.jpg" 
        alt="CompreFace Face Detection Demo" width=390px style="padding: 0px 10px 0px 0px;">
</a>
<a target="_blank" href="https://www.youtube.com/watch?v=jkiA3S-LYSk">
     <img src="https://user-images.githubusercontent.com/3736126/242002411-3c06d3f7-c0ac-49f8-ac79-42bd8c431570.png" 
        alt="CompreFace Appery.io Demo" width=390px style="padding: 0px 10px 0px 0px;">
</a>
</p>

<details>
  <summary> <b>More Videos</b> </summary>
  <!-- have to be followed by an empty line! -->

<p align="center">
<a target="_blank" href="https://www.youtube.com/watch?v=cF3P7bTJXY0">
     <img src="https://user-images.githubusercontent.com/3736126/241274256-0dc6d8a0-91d5-42c4-b029-200b72bb169b.jpg" 
        alt="CompreFace .NET SDK Demo" width=390px style="padding: 0px 10px 0px 0px;">
</a>
<a target="_blank" href="https://www.youtube.com/watch?v=9mQULPrTVP4">
     <img src="https://user-images.githubusercontent.com/3736126/241274522-a152221f-e382-416c-9a71-f7694e73cf3e.jpg" 
        alt="CompreFace JavaScript SDK Demo" width=390px style="padding: 0px 10px 0px 0px;">
</a>
</p>

</details>

# News and updates

[Subscribe](https://info.exadel.com/en/compreface-news-and-updates) to CompreFace News and Updates to never miss new features and product improvements.

# Features
The Moroccan Airborne Troops Face Recognition System provides military-grade biometric identification capabilities. System can accurately identify personnel even from a single enrollment photo.

**Security Features:**
- Complete offline operation for air-gapped military networks
- Military-grade encryption and data security
- Self-hosted on military infrastructure - no external dependencies
- Unauthorized intruder detection with instant alerts
- Multi-level access control (Unit, Battalion, Brigade levels)
- Comprehensive audit trail for all access attempts

**Performance & Scalability:**
- M3 Max GPU acceleration with MPS support (4-6x performance boost)
- Supports both CPU and GPU deployment
- Scalable across multiple military units (300-500 personnel per unit)
- Real-time multi-face detection and recognition
- Hikvision 8MP military-grade camera integration
- State-of-the-art AI models (FaceNet, InsightFace)

**Deployment:**
- Quick deployment with single docker command
- Portable deployment for field operations
- Low-power consumption for mobile deployments
- MacBook M3 Max optimized for command centers
- Works in harsh environmental conditions

# Functionalities

- Supports many face recognition services:
  - [face detection](/docs/Face-services-and-plugins.md#face-detection)
  - [face recognition](/docs/Face-services-and-plugins.md#face-recognition)
  - [face verification](/docs/Face-services-and-plugins.md#face-verification)
  - [landmark detection plugin](/docs/Face-services-and-plugins.md#face-plugins)
  - [age recognition plugin](/docs/Face-services-and-plugins.md#face-plugins)
  - [gender recognition plugin](/docs/Face-services-and-plugins.md#face-plugins)
  - [face mask detection plugin](/docs/Face-services-and-plugins.md#face-plugins)
  - [head pose plugin](/docs/Face-services-and-plugins.md#face-plugins)
- Use the CompreFace UI panel for convenient user roles and access management

# Getting Started with CompreFace

### Requirements

1. Docker and Docker compose (or Docker Desktop)
2. CompreFace could be run on most modern computers with [x86 processor](https://en.wikipedia.org/wiki/X86) and [AVX support](https://en.wikipedia.org/wiki/Advanced_Vector_Extensions).
   To check AVX support on Linux run `lscpu | grep avx` command

### To get started (Linux, MacOS):

1. Install Docker and Docker Compose
2. Download the archive from our latest release: https://github.com/exadel-inc/CompreFace/releases
3. Unzip the archive
4. Open the terminal in this folder and run this command: `docker-compose up -d`
5. Open the service in your browser: http://localhost:8000/login

### To get started (Windows):

1. Install Docker Desktop
2. Download the archive from our latest release: https://github.com/exadel-inc/CompreFace/releases
3. Unzip the archive
4. Run Docker
5. Open Command prompt (write `cmd` in windows search bar)
6. Open folder where you extracted zip archive (Write `cd path_of_the_folder`, press enter).
7. Run command: `docker-compose up -d`
8. Open http://localhost:8000/login

### Getting started for contributors

Follow this [link](/dev)

# CompreFace SDKs

| SDK        | Repository                                              |
|------------|---------------------------------------------------------|
| JavaScript | https://github.com/exadel-inc/compreface-javascript-sdk |
| Python     | https://github.com/exadel-inc/compreface-python-sdk     |
| .NET       | https://github.com/exadel-inc/compreface-net-sdk        |

# Documentation

More documentation is available [here](/docs)

# Contributing

We want to improve our open-source face recognition solution, so your contributions are welcome and greatly appreciated. 

* Just use CompreFace and [report](https://github.com/exadel-inc/CompreFace/issues) ideas and bugs on GitHub
* Share knowledge and experience via posting guides and articles, or just improve our [documentation](https://github.com/exadel-inc/CompreFace/tree/master/docs)
* Create [SDKs](https://github.com/topics/compreface-sdk) for favorite programming language, we will add it to our documentation
* Integrate CompreFace support to other platforms like [Home Assistant](https://www.home-assistant.io/) or [DreamFactory](https://www.dreamfactory.com/), we will add it to our documentation
* [Contribute](CONTRIBUTING.md) code
* Add [plugin](/docs/Face-services-and-plugins.md#face-plugins) to face services
* And last, but not least, you can just give a star to our free facial recognition system on GitHub

For more information, visit our [contributing](CONTRIBUTING.md) guide, or create a [discussion](https://github.com/exadel-inc/CompreFace/discussions).

# License info 

CompreFace is open-source real-time facial recognition software released under the [Apache 2.0 license](https://www.apache.org/licenses/LICENSE-2.0.html).
