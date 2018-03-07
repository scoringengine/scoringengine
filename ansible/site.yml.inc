---
- name: Deploy Scoring Engine
  hosts: scoring_engine
  remote_user: root
  roles:
    - ansible-scoringengine-role
