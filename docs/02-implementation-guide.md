# The Unique Value of AT4DX: Practical Implementation Guide

AT4DX (Advanced Techniques for Adopting Salesforce DX Unlocked Packages) extends the capabilities of fflib common, fflib mocks, and force-di by providing a comprehensive framework specifically designed for modular application development in Salesforce DX unlocked packages. This guide provides concrete implementation examples and best practices for architects, DevOps engineers, and developers.

## 1. Dependency Injection Integration with Enterprise Patterns

### For Architects
AT4DX replaces static method calls in traditional fflib with dependency injection, providing several architectural benefits:

- **Metadata-Driven Class Factory**: Classes are registered via Custom Metadata records rather than hard-coded in Apex
- **Package Modularity**: Each package can register its own implementations without modifying base code

**Example**: The Account SObject binding in reference-implementation-common package:

```xml
<!-- ApplicationFactory_DomainBinding.AccountSObjectBinding.md-meta.xml -->
<CustomMetadata xmlns="http://soap.sforce.com/2006/04/metadata">
    <label>AccountSObjectBinding</label>
    <protected>false</protected>
    <values>
        <field>BindingSObject__c</field>
        <value xsi:type="xsd:string">Account</value>
    </values>
    <values>
        <field>To__c</field>
        <value xsi:type="xsd:string">Accounts.Constructor</value>
    </values>
</CustomMetadata>
```

### For Developers
Instead of using the traditional fflib static factory approach, use Application class with dependency injection:

```java
// Traditional fflib
fflib_ISObjectDomain domain = Application.Domain.newInstance(accounts);

// AT4DX way - functionally similar but uses DI under the hood
IApplicationSObjectDomain domain = Application.Domain.newInstance(accounts);
```

The key difference is that in AT4DX, the binding is configured via metadata rather than hard-coded in Apex, allowing package modularity.

### For DevOps Engineers
Configure CI/CD to deploy CustomMetadata records during package installation. DI bindings enable modular deployment without requiring modification to base code:

```yaml
# GitHub Actions workflow example (.github/workflows/deploy.and.test.yml)
- name: Install required dependency frameworks
  run: sf shane github src install --convert --githubuser apex-enterprise-patterns --repo fflib-apex-mocks
- run: sf shane github src install --convert --githubuser apex-enterprise-patterns --repo fflib-apex-common
- run: sf shane github src install --convert --githubuser apex-enterprise-patterns --repo force-di
- run: sf shane github src install --convert --githubuser apex-enterprise-patterns --repo at4dx
```

## 2. Domain Process Injection

### For Architects
Domain Process Injection allows extending behavior of domain objects without modifying their code, implementing a true plugin architecture:

- Domain objects become extension points rather than implementation containers
- Different packages can contribute behavior to the same SObject
- Behavior can be conditionally applied based on configurable criteria

**Example Architecture**: In the sample code, the marketing package adds a feature to Account objects (created in common package) to set a slogan when the Account name contains "Fish", without modifying the Account domain class.

### For Developers
Instead of modifying domain code directly, create separate criteria and action classes:

**Criteria Class**:
```java
// AccountNameContainsFishCriteria.cls
public class AccountNameContainsFishCriteria
    implements IDomainProcessCriteria
{
    private list<Account> records = new list<Account>();

    public IDomainProcessCriteria setRecordsToEvaluate(List<SObject> records)
    {
        this.records.clear();
        this.records.addAll((list<Account>)records);
        return this;
    }

    public List<SObject> run()
    {
        list<Account> qualifiedRecords = new list<Account>();
        for (Account record : this.records)
        {
            if (record.Name.containsIgnoreCase('fish'))
            {
                qualifiedRecords.add(record);
            }
        }
        return qualifiedRecords;
    }
}
```

**Action Class**:
```java
// DefaultAccountSloganBasedOnNameAction.cls
public class DefaultAccountSloganBasedOnNameAction 
    extends DomainProcessAbstractAction
{
    public override void runInProcess()
    {
        for (SObject record : this.records)
        {
            Account accountRecord = (Account)record;
            accountRecord.Slogan__c = accountRecord.name + ' is a fishy business';
        }
    }
}
```

**Custom Metadata to Wire It Up**:
```xml
<!-- DomainProcessBinding.FishCompanySlogans10_10Criteria.md-meta.xml -->
<CustomMetadata xmlns="http://soap.sforce.com/2006/04/metadata">
    <label>Fish Company Slogans Criteria 1</label>
    <values>
        <field>ClassToInject__c</field>
        <value xsi:type="xsd:string">AccountNameContainsFishCriteria</value>
    </values>
    <values>
        <field>ProcessContext__c</field>
        <value xsi:type="xsd:string">TriggerExecution</value>
    </values>
    <values>
        <field>RelatedDomainBindingSObject__c</field>
        <value xsi:type="xsd:string">Account</value>
    </values>
    <values>
        <field>TriggerOperation__c</field>
        <value xsi:type="xsd:string">Before_Insert</value>
    </values>
    <values>
        <field>Type__c</field>
        <value xsi:type="xsd:string">Criteria</value>
    </values>
</CustomMetadata>
```

### For DevOps Engineers
Create package dependencies so that extension packages are installed after the base package. Use the dependency injection patterns to configure order of execution across packages:

```json
// sfdx-project.json (excerpt)
{
  "packageDirectories": [
    { "path": "sfdx-source/reference-implementation-common", "default": false },
    { "path": "sfdx-source/reference-implementation-marketing", "default": false },
    { "path": "sfdx-source/reference-implementation-sales", "default": false }
  ]
}
```

## 3. Platform Event Distribution Framework

### For Architects
AT4DX provides a configurable, metadata-driven approach to route platform events:

- Events become a formal cross-package communication channel
- Loose coupling between event publishers and consumers 
- Packages can subscribe to events without the publishing package being aware

### For Developers
**Create Event Publisher**:
```java
// AccountModsEventPublisher.cls
public class AccountModsEventPublisher {
    public static void publishAccountModification(Set<Id> accountIds) {
        EventBus.publish(new AT4DXMessage__e(
            Category__c = 'Account',
            EventName__c = 'ACCOUNT_RECORD_MODIFICATION',
            Payload__c = JSON.serialize(accountIds)
        ));
    }
}
```

**Create Event Consumer**:
```java
// Sales_PlatformEventsConsumer.cls
public class Sales_PlatformEventsConsumer extends PlatformEventAbstractConsumer {
    public override void runInProcess() {
        Set<Id> accountIdSet = new Set<Id>();
        for (SObject sobj : events) {
            AT4DXMessage__e evt = (AT4DXMessage__e) sobj;
            accountIdSet.addAll((Set<Id>) JSON.deserialize(evt.Payload__c, Set<Id>.class));
        }
        Sales_AccountsService.proocessAccountChanges(accountIdSet);
    }
}
```

**Configure Subscription via Metadata**:
```xml
<!-- PlatformEvents_Subscription.Sales_PlatformEventsConsumer.md-meta.xml -->
<CustomMetadata xmlns="http://soap.sforce.com/2006/04/metadata">
    <label>Sales_PlatformEventsConsumer</label>
    <values>
        <field>Consumer__c</field>
        <value xsi:type="xsd:string">Sales_PlatformEventsConsumer</value>
    </values>
    <field>EventBus__c</field>
    <value xsi:type="xsd:string">AT4DXMessage__e</value>
    </values>
    <values>
        <field>EventCategory__c</field>
        <value xsi:type="xsd:string">Account</value>
    </values>
    <values>
        <field>Event__c</field>
        <value xsi:type="xsd:string">ACCOUNT_RECORD_MODIFICATION</value>
    </values>
    <values>
        <field>MatcherRule__c</field>
        <value xsi:type="xsd:string">MatchEventBusAndCategoryAndEventName</value>
    </values>
</CustomMetadata>
```

### For DevOps Engineers
Deploy platform event definitions as part of the core package. Ensure triggers for the AT4DXMessage__e and AT4DXImmediateMessage__e events are in place for the distribution framework to function:

```xml
<!-- AT4DXMessages.trigger -->
trigger AT4DXMessages on AT4DXMessage__e (after insert) {
    PlatformEventDistributor.triggerHandler();
}
```

## 4. Selector Method Injection

### For Architects
AT4DX allows selectors to dynamically include fields from different packages:

- Base selectors can be enhanced with fields from extension packages
- No code modification required to base selectors
- Fieldsets provide a familiar configuration mechanism

### For Developers
**Create a fieldset in your extension package**:
```xml
<!-- SelectorInclusion_AccountFieldsMarketing.fieldSet-meta.xml -->
<FieldSet xmlns="http://soap.sforce.com/2006/04/metadata">
    <fullName>SelectorInclusion_AccountFieldsMarketing</fullName>
    <displayedFields>
        <field>Slogan__c</field>
        <isFieldManaged>false</isFieldManaged>
        <isRequired>false</isRequired>
    </displayedFields>
    <label>Selector Inclusion Account Marketing</label>
</FieldSet>
```

**Add metadata to register the fieldset for inclusion**:
```xml
<!-- SelectorConfig_FieldSetInclusion.AccountFieldsFromMarketing.md-meta.xml -->
<CustomMetadata xmlns="http://soap.sforce.com/2006/04/metadata">
    <label>Accounts Fields From Marketing Package</label>
    <values>
        <field>FieldsetName__c</field>
        <value xsi:type="xsd:string">SelectorInclusion_AccountFieldsMarketing</value>
    </values>
    <values>
        <field>BindingSObject__c</field>
        <value xsi:type="xsd:string">Account</value>
    </values>
</CustomMetadata>
```

**The base selector automatically includes these fields**:
```java
// AccountsSelector.cls (in common package)
public List<Account> selectByName(Set<String> nameSet) {
    fflib_QueryFactory qf = newQueryFactory();
    
    // This for loop includes fields from all registered fieldsets
    for (FieldSet fs : sObjectFieldSetList) {
        qf.selectFieldSet(fs);
    }

    qf.setCondition(Account.Name + ' in :nameSet');
    return Database.query(qf.toSOQL());
}
```

### For DevOps Engineers
Ensure fieldset metadata is deployed before the selector is executed. Include permission sets to grant access to the new fields:

```xml
<!-- MarketingPackageSObjectsAndFieldsVIEW.permissionset-meta.xml -->
<PermissionSet xmlns="http://soap.sforce.com/2006/04/metadata">
    <fieldPermissions>
        <editable>false</editable>
        <field>Account.Slogan__c</field>
        <readable>true</readable>
    </fieldPermissions>
    <!-- other permissions -->
</PermissionSet>
```

## 5. Test Data Supplementer

### For Architects
AT4DX provides a mechanism for extension packages to supplement test data with their own fields:

- Test data creation is decentralized
- Each package is responsible for populating its own fields
- Avoids hard dependencies in test classes

### For Developers
**Create a test data supplementer for your fields**:
```java
// MarketingFieldsForAccountsSupplementer.cls
@IsTest
public class MarketingFieldsForAccountsSupplementer
    implements ITestDataSupplement
{
    public void supplement(List<SObject> accountSObjectList)
    {
        for (Account acct : (List<Account>) accountSObjectList)
        {
            acct.Slogan__c = 'Hello world!';
        }
    }
}
```

**Register the supplementer via metadata**:
```xml
<!-- TestDataSupplementer.Account_ReferenceImplementation.md-meta.xml -->
<CustomMetadata xmlns="http://soap.sforce.com/2006/04/metadata">
    <label>Account Supplementer for Reference Implementation</label>
    <values>
        <field>BindingSObject__c</field>
        <value xsi:type="xsd:string">Account</value>
    </values>
    <values>
        <field>SupplementingClass__c</field>
        <value xsi:type="xsd:string">MarketingFieldsForAccountsSupplementer</value>
    </values>
</CustomMetadata>
```

**Use the supplementer in tests**:
```java
// In test classes
List<Account> accounts = new List<Account>{
    new Account(Name = 'Test Account 1'),
    new Account(Name = 'Test Account 2')
};
TestDataSupplementer.supplement(accounts);
// Now the accounts have Slogan__c populated with 'Hello world!'
```

### For DevOps Engineers
Ensure test classes that rely on fields from multiple packages include the proper supplementers. Configure CI/CD to run tests in the correct order, after all packages are deployed:

```yaml
# GitHub Actions workflow (excerpt)
- name: Deploy and compile the codebase
  run: sf project deploy start
- name: Run the tests
  run: sf apex run test --wait 5
```

## 6. Unlocked Package-Specific Architecture

### For Architects
The AT4DX sample code demonstrates a modular architecture across multiple packages:

- **reference-implementation-common**: Base domain objects, selectors, and services
- **reference-implementation-marketing**: Marketing-specific extensions
- **reference-implementation-sales**: Sales-specific extensions
- **reference-implementation-service**: Service-specific extensions

### For Developers
Develop features in isolation within package boundaries:
```
reference-implementation-common
├── domains
│   └── Accounts.cls (base domain)
└── selectors
    └── AccountsSelector.cls (base selector)

reference-implementation-marketing
├── actions
│   └── DefaultAccountSloganBasedOnNameAction.cls
├── criteria
│   └── AccountNameContainsFishCriteria.cls
└── schema
    └── objects
        └── Account
            └── fields
                └── Slogan__c.field-meta.xml
```

### For DevOps Engineers
Configure package dependencies in sfdx-project.json for proper installation order:

```json
{
  "packageDirectories": [
    {
      "path": "sfdx-source/reference-implementation-common",
      "package": "Reference Implementation Common",
      "versionNumber": "1.0.0.NEXT",
      "default": false
    },
    {
      "path": "sfdx-source/reference-implementation-marketing",
      "package": "Reference Implementation Marketing",
      "versionNumber": "1.0.0.NEXT",
      "dependencies": [
        {
          "package": "Reference Implementation Common",
          "versionNumber": "1.0.0.LATEST"
        }
      ]
    }
    // Additional packages
  ]
}
```

## 7. Reduced Coupling Between Packages

### For Architects
The AT4DX architecture reduces coupling using:

- Interface-based programming with DI for implementation
- Event-based communication between packages
- Metadata-driven configuration

### For Developers
Use interfaces for all cross-package interactions:

```java
// IAccountsService.cls (in common package)
public interface IAccountsService {
    void processAccounts(Set<Id> accountIds);
}

// Sales_AccountsService.cls (in sales package)
public class Sales_AccountsService implements IAccountsService {
    public void processAccounts(Set<Id> accountIds) {
        // Implementation
    }
}
```

Register implementations using metadata:
```xml
<!-- ApplicationFactory_ServiceBinding.IAccountsServiceBinding.md-meta.xml -->
<CustomMetadata xmlns="http://soap.sforce.com/2006/04/metadata">
    <label>IAccountsServiceBinding</label>
    <values>
        <field>BindingInterface__c</field>
        <value xsi:type="xsd:string">IAccountsService</value>
    </values>
    <values>
        <field>To__c</field>
        <value xsi:type="xsd:string">Sales_AccountsService</value>
    </values>
</CustomMetadata>
```

### For DevOps Engineers
Create a package dependency matrix to document and enforce dependencies. Implement validation in CI/CD to prevent circular dependencies:

```
Core AT4DX Package ← fflib-apex-common ← fflib-apex-mocks ← force-di
    ↑
Reference Implementation Common
    ↑
Reference Implementation Marketing, Sales, Service (parallel dependencies)
```

## 8. Advanced Testing Support

### For Architects
Design for testability with:
- Clear package boundaries
- Interface-based mocking
- Supplementation of test data

### For Developers
Use dependency injection for easy mocking:

```java
// AccountsServiceTest.cls
@IsTest
private class AccountsServiceTest {
    @IsTest
    static void testProcessAccount() {
        // Mock setup
        IAccountsSelector mockSelector = (IAccountsSelector)
            Application.Selector.setMock(Accounts.SObjectType, new MockAccountsSelector());
        
        // Test execution
        Test.startTest();
        IAccountsService service = (IAccountsService)Application.Service.newInstance(IAccountsService.class);
        service.processAccounts(new Set<Id>{fflib_IDGenerator.generate(Account.SObjectType)});
        Test.stopTest();
        
        // Assertions
        System.assertEquals(1, mockSelector.selectById().size());
    }
    
    // Mock implementation
    private class MockAccountsSelector implements IAccountsSelector {
        public Schema.SObjectType getSObjectType() {
            return Account.SObjectType;
        }
        
        public List<Account> selectById(Set<Id> idSet) {
            return new List<Account>{new Account(Id = idSet.iterator().next(), Name = 'Test')};
        }
    }
}
```

### For DevOps Engineers
Configure CI/CD to run tests from each package and test cross-package integration. Use test data supplementation to reduce test maintenance:

```yaml
# GitHub Actions workflow (excerpt)
- name: Run tests for common package
  run: sf apex run test --tests AccountsServiceTest --wait 5
- name: Run tests for marketing package
  run: sf apex run test --tests AccountSloganRelatedTest --wait 5
```

## Conclusion

AT4DX takes the solid foundation of fflib and force-di to the next level by providing a comprehensive framework specifically designed for modular enterprise development with Salesforce DX unlocked packages. Its unique value lies in enabling true separation of concerns, modular extension points, and cross-package communication while maintaining the familiar patterns of fflib. This makes it an ideal choice for large, complex Salesforce implementations with multiple teams working on different functional areas that need to interact with shared data models.
