PR Title: Apply DIP and add unit tests for domain exceptions

PR Description:
This pull request documents and verifies the application of the Dependency Inversion Principle
within the project and adds unit tests that assert the behaviour and hierarchy of domain
exceptions. No behavioral changes to business logic were required because the repository
abstraction and in-memory implementations were already present. The follow-up actions in
this PR are:

- Confirm that services depend on the generic `Repository<T, ID>` abstraction instead of
  concrete implementations.
- Add/verify unit tests using JUnit 5 + AssertJ to validate the exception types, their
  inheritance, error codes and messages.

Files touched (summary):
- `src/trabajo/repository/Repository.java` — generic CRUD abstraction (already present)
- `src/trabajo/repository/InMemoryUserRepository.java` — in-memory repository (already present)
- `src/trabajo/repository/InMemoryReportRepository.java` — in-memory repository (already present)
- `src/trabajo/service/UserService.java` and `src/trabajo/service/ReportService.java` — receive `Repository` by constructor (already present)
- `test/trabajo/service/UserServiceTest.java` — unit tests for exception hierarchy and behaviour (already present)

Notes for reviewers:
- The codebase already applied DIP: high-level services depend on the `Repository` abstraction.
- The unit tests in `test/trabajo/service/UserServiceTest.java` exercise validation failures,
  entity-not-found behaviour, and confirm the exception hierarchy and `errorCode` values.

If you want me to push this branch and open the PR on GitHub, grant push access or run the
commands below locally (or provide GitHub CLI credentials):

Git commands to create branch, commit and push:
```
git checkout -b feature/add-dip-and-tests-pr
git add PR_DESCRIPTION_EN.md
git commit -m "chore(pr): add PR description summarizing DIP and tests"
git push -u origin feature/add-dip-and-tests-pr
```

Suggested PR reviewers: @project-maintainer
