"""BIOWIKI test package.

Tests never insert TEST FIXTURE records into the production PostgreSQL
dataset. Unit tests use in-memory objects. Database and API tests are
read-only against the live scientific data.
"""
