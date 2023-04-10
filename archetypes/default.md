---
title: "{{ replace .TranslationBaseName "-" " " | title }}"
date: {{ .Date }}
author: "{{ index $.Site.Params.lang.author $.Section}}"
slug:
draft: false
keywords: 
- 
description: 
toc: false
tag:
---
