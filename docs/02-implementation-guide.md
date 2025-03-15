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

**Explanation**

This is an `ApplicationFactory_DomainBinding__mdt` custom metadata record named "AccountSObjectBinding" that creates a binding between the Account SObject and its domain implementation.

Breaking it down:

1. `label` defines the display name of this metadata record as "AccountSObjectBinding"

2. `protected` set to "false" means this metadata record can be modified by administrators

3. The `BindingSObject__c` field specifies which SObject this binding applies to - in this case, "Account"

4. The `To__c` field specifies the implementation class that should be instantiated when code requests a domain for Account objects - "Accounts.Constructor"

In AT4DX, the notation "Accounts.Constructor" refers to a static inner class named "Constructor" within the "Accounts" domain class that implements the fflib_SObjectDomain.IConstructable interface.

This metadata-driven approach is what allows AT4DX to use dependency injection instead of hardcoded class references. When code calls `Application.Domain.newInstance(accountRecords)`, the framework:

1. Looks up the SObject type of the records (Account)
2. Searches for a matching ApplicationFactory_DomainBinding__mdt record
3. Finds this binding pointing to "Accounts.Constructor"
4. Instantiates that class and passes the records to it
5. Returns the resulting domain object

The key advantage is that different packages can provide their own bindings without modifying existing code. For example, a finance package could override the Account domain implementation with a specialized version by creating a new binding with higher priority.

This approach decouples the consumer of a domain from its implementation, allowing for modular, extensible architecture across package boundaries.

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

This is a `DomainProcessBinding__mdt` record named "FishCompanySlogans10_10Criteria" that defines criteria that should be executed during Account trigger processing.

Breaking it down:

1. `label` - "Fish Company Slogans Criteria 1" is the human-readable name for this process binding

2. `ClassToInject__c` - "AccountNameContainsFishCriteria" identifies the Apex class that implements the criteria logic. This class would implement the `IDomainProcessCriteria` interface and contains the actual filter logic.

3. `ProcessContext__c` - "TriggerExecution" specifies that this binding applies during trigger execution (as opposed to being called from domain methods directly).

4. `RelatedDomainBindingSObject__c` - "Account" indicates this binding applies to the Account SObject.

5. `TriggerOperation__c` - "Before_Insert" specifies that this binding should execute during the before insert trigger phase of Account records.

6. `Type__c` - "Criteria" identifies this as a criteria binding rather than an action binding. In AT4DX, criteria classes filter records to determine which ones should be processed by subsequent actions.

Here's what happens at runtime:

1. When Account records are inserted, the Account trigger fires.
2. The Domain Process Coordinator, which is configured in the trigger, scans for all applicable DomainProcessBinding__mdt records.
3. It finds this criteria binding for "Before_Insert" operations.
4. It instantiates the "AccountNameContainsFishCriteria" class.
5. The criteria class examines each Account record to see if its name contains "fish".
6. Only records meeting this criteria are passed on to the next step in the process.

In the AT4DX sample code, there's likely a corresponding action binding with a similar name (like FishCompanySlogans10_20Action) that would process the filtered records by setting a slogan field.

This approach is powerful because:

1. The marketing package can inject behavior into the Account object without modifying its base domain code.
2. The filter logic is encapsulated in a dedicated class rather than mixed with processing logic.
3. The whole process is configured via metadata rather than code, allowing for changes without deployment.
4. Multiple packages can contribute different criteria and actions, all executed in the proper order based on their OrderOfExecution__c values.

This exemplifies AT4DX's ability to extend functionality across package boundaries in a modular, loosely coupled way.

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

The `AccountModsEventPublisher` class provides a standardized way to publish platform events when Account records are modified.  This class acts as a publisher in the publish-subscribe pattern for cross-package communication in AT4DX. Here's how it works:

1. It exposes a static method `publishAccountModification` that takes a Set of Account Ids as input.

2. Inside the method, it creates a new platform event of type `AT4DXMessage__e`, which is a standard event type provided by AT4DX.

3. It populates three standard fields on the platform event:
   - `Category__c`: Set to 'Account' to categorize this event as Account-related
   - `EventName__c`: Set to 'ACCOUNT_RECORD_MODIFICATION' to specifically identify the type of event
   - `Payload__c`: Contains the serialized set of Account Ids that were modified

4. Finally, it publishes the event to the platform event bus using the standard Salesforce `EventBus.publish()` method.

This approach has several benefits:

1. **Loose Coupling**: The publisher doesn't need to know who will consume these events. Any package that wants to react to Account modifications can subscribe to these events without the publisher being aware.

2. **Standardized Structure**: By using the AT4DX standard event structure with Category, EventName, and Payload fields, it follows a consistent pattern that the AT4DX Platform Event Distributor can route appropriately.

3. **Cross-Package Communication**: This enables different packages to communicate without direct dependencies. For example, the Sales package can subscribe to these events even though it doesn't depend on the package that publishes them.

4. **Asynchronous Processing**: Using platform events enables asynchronous processing of Account changes, which can help with governor limits and processing isolation.

In practice, this class would be called from within domain logic or service methods when Account records are modified, triggering the event that other packages can then respond to.


#### **AT4DXMessage__e**: A Generic Platform Event as a Event Bus

It's designed as a single, flexible platform event that can support many different types of events across your application through its structured fields.

It serves as a generic event bus with three key fields:

1. **Category__c**: Identifies the broad category of the event (like 'Account', 'Opportunity', 'System', etc.). This allows subscribers to filter for events related to specific areas of functionality.

2. **EventName__c**: Provides a more specific identifier for the event type within a category (like 'ACCOUNT_RECORD_MODIFICATION', 'OPPORTUNITY_STAGE_CHANGE', etc.). This gives fine-grained control over what specific events to subscribe to.

3. **Payload__c**: Contains the event data serialized as JSON. This flexible approach means any structured data can be passed through the same event type - from simple IDs to complex data structures.

This design brings several benefits:

- **Consolidated Event Management**: Instead of creating dozens of custom platform event types for different scenarios, you use one consistent type with standardized fields.

- **Dynamic Subscription**: AT4DX's PlatformEventDistributor can route events to the appropriate consumers based on rules defined in metadata (PlatformEvents_Subscription__mdt records).

- **Simplified Governance**: Managing a single platform event type is easier than maintaining many different event definitions.

- **Matching Flexibility**: The PlatformEventDistributor supports different matching rules like matching on category only, event name only, or both together.

The sample code also includes AT4DXImmediateMessage__e, which works the same way but is processed in the current transaction context rather than asynchronously.

This architecture means new events can be added without creating new platform event definitions - you simply use new Category/EventName combinations and document them as part of your application's event catalog.

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

This CustomMetadata record is a subscription configuration for AT4DX's Platform Event Distribution framework. This is a `PlatformEvents_Subscription__mdt` record named "Sales_PlatformEventsConsumer" that registers a consumer to process specific platform events. 

Breaking it down:

1. `label` - "Sales_PlatformEventsConsumer" is the human-readable name for this subscription.

2. `Consumer__c` - "Sales_PlatformEventsConsumer" is the name of the Apex class that will handle the events. This class must implement the `IEventsConsumer` interface or extend `PlatformEventAbstractConsumer`.

3. `EventBus__c` - "AT4DXMessage__e" identifies which platform event object this subscription applies to. This corresponds to the generic event bus provided by AT4DX.

4. `EventCategory__c` - "Account" specifies that this consumer is only interested in events with the Category__c field set to "Account". 

5. `Event__c` - "ACCOUNT_RECORD_MODIFICATION" further restricts this subscription to only handle events with this specific event name.

6. `MatcherRule__c` - "MatchEventBusAndCategoryAndEventName" tells the PlatformEventDistributor to use all three criteria (event bus, category, and event name) when determining if an event should be routed to this consumer.

Here's what happens at runtime:

1. When an AT4DXMessage__e platform event is published (e.g., via AccountModsEventPublisher), it triggers the AT4DXMessages trigger.

2. The trigger calls PlatformEventDistributor.triggerHandler() which processes all incoming events.

3. The distributor looks up all registered PlatformEvents_Subscription__mdt records.

4. It evaluates each event against each subscription using the specified matcher rule.

5. For this subscription, it will check if:
   - The event is an AT4DXMessage__e
   - Category__c equals "Account"
   - EventName__c equals "ACCOUNT_RECORD_MODIFICATION"

6. If all conditions match, it instantiates the Sales_PlatformEventsConsumer class and passes the matching events to it for processing.

This approach enables the Sales package to listen for Account modification events without direct dependencies on the publishing package. The subscription is entirely configured via metadata, making it possible to add or modify event handling without code changes.

This is a powerful example of how AT4DX enables modular, loosely coupled architecture through metadata-driven configuration.

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

This XML file defines a Salesforce FieldSet that is a key part of AT4DX's Selector Field Injection mechanism. This FieldSet is named `SelectorInclusion_AccountFieldsMarketing` and it's designed to be used with the Account object. It's created in the marketing package to extend the account selector with marketing-specific fields.

Breaking it down:

1. `fullName` - "SelectorInclusion_AccountFieldsMarketing" is the API name of the FieldSet.

2. `displayedFields` - This section lists all fields that should be included in this FieldSet:
   - `field` - "Slogan__c" is a custom field from the marketing package that should be included in queries
   - `isFieldManaged` - "false" indicates this field isn't managed by a package
   - `isRequired` - "false" means this field isn't required to be populated

3. `label` - "Selector Inclusion Account Marketing" is the human-readable name for this FieldSet.

Why this is important:

In traditional fflib, to add fields to a selector, you would need to modify the selector class directly by adding the new fields to the getSObjectFieldList() method. This creates tight coupling between packages and makes it hard to modularly extend functionality.

AT4DX solves this problem with FieldSets and the following mechanism:

1. The marketing package defines this FieldSet containing marketing-specific fields for Account.

2. It then creates a `SelectorConfig_FieldSetInclusion__mdt` record that registers this FieldSet with the AT4DX framework. See "Add metadata to register the fieldset for inclusion" below. 

3. The core AccountsSelector includes code to dynamically add all registered FieldSets. See "The base selector automatically includes these fields".below 

This powerful pattern allows:
- Different packages to add their own fields to existing selectors
- No modification of base selector code
- Clean separation of concerns
- Modular deployment where packages can be installed or uninstalled without breaking selectors

This is one of the key ways AT4DX enables true modular development across package boundaries while maintaining the familiar Selector pattern from fflib.

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

## How Multiple Service Implementations Are Handled

When you have multiple classes implementing the same `IAccountsService` interface across different packages in AT4DX, how these implementations are used depends on how they're registered via dependency injection. Here are the AT4DX options for handling multiple implementations of the same interface:

### 1. Default Binding with Priority

Each implementation is registered with a Custom Metadata record:

```xml
<!-- From Sales Package -->
<CustomMetadata>
    <label>IAccountsService_Sales</label>
    <values>
        <field>BindingInterface__c</field>
        <value>IAccountsService</value>
    </values>
    <values>
        <field>To__c</field>
        <value>Sales_AccountsService</value>
    </values>
    <values>
        <field>Priority__c</field>
        <value>10</value>
    </values>
</CustomMetadata>

<!-- From Marketing Package -->
<CustomMetadata>
    <label>IAccountsService_Marketing</label>
    <values>
        <field>BindingInterface__c</field>
        <value>IAccountsService</value>
    </values>
    <values>
        <field>To__c</field>
        <value>Marketing_AccountsService</value>
    </values>
    <values>
        <field>Priority__c</field>
        <value>20</value>
    </values>
</CustomMetadata>
```

When code calls:
```java
IAccountsService service = (IAccountsService)Application.Service.newInstance(IAccountsService.class);
```

Only ONE implementation will be returned - the one with the highest priority value. In this example, `Marketing_AccountsService` would be used because its priority (20) is higher than `Sales_AccountsService` (10).

### 2. Named Bindings

Instead of relying on priority, you can use named bindings:

```java
// Get specifically the Sales implementation
IAccountsService salesService = (IAccountsService)Application.Service.newInstance(IAccountsService.class, 'Sales');

// Get specifically the Marketing implementation
IAccountsService marketingService = (IAccountsService)Application.Service.newInstance(IAccountsService.class, 'Marketing');
```

This requires appropriate binding configuration with named parameters.

### 3. Service Aggregation Pattern

You can create a composite service that delegates to all registered implementations:

```java
public class CompositeAccountsService implements IAccountsService {
    public void processAccounts(Set<Id> accountIds) {
        // Get all implementations
        List<IAccountsService> allServices = di_Injector.Org.getAll(IAccountsService.class);
        
        // Call each implementation
        for(IAccountsService service : allServices) {
            service.processAccounts(accountIds);
        }
    }
}
```

This composite service would then be registered as the primary binding.

### 4. Event-Based Communication

Instead of directly calling services, different implementations can subscribe to events:

```java
// Publisher code
EventBus.publish(new AT4DXMessage__e(
    Category__c = 'Account',
    EventName__c = 'PROCESS_ACCOUNTS',
    Payload__c = JSON.serialize(accountIds)
));
```

Each service then has its own consumer class that subscribes to this event. This is the most loosely coupled approach and is often preferred in AT4DX for cross-package communication.

## Best Practices

In AT4DX, the preferred approach for handling multiple implementations across packages is usually:

1. For independent behavior - Use the event-based approach where each package responds to events independently
2. For explicit composition - Use a higher-level service that explicitly orchestrates calls to specific named implementations
3. For override/priority behavior - Use priority-based bindings where one implementation should take precedence

This modular approach is one of the key advantages of AT4DX's dependency injection framework over traditional fflib, where managing multiple implementations would require more custom code.

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

This `AccountsServiceTest` is demonstrating unit testing with AT4DX's dependency injection framework. The purpose of this test is to verify that the `AccountsService` implementation correctly processes accounts while using mocking to isolate the test from database dependencies.  Let's break down what's happening:

1. **Mocking Dependencies**: 
   ```java
   IAccountsSelector mockSelector = (IAccountsSelector)
       Application.Selector.setMock(Accounts.SObjectType, new MockAccountsSelector());
   ```
   This line creates a mock implementation of the `IAccountsSelector` interface and registers it with the AT4DX dependency injection framework. This means any code that requests an `IAccountsSelector` for Account records will receive this mock instead of the real implementation.

2. **Test Execution**:
   ```java
   IAccountsService service = (IAccountsService)Application.Service.newInstance(IAccountsService.class);
   service.processAccounts(new Set<Id>{fflib_IDGenerator.generate(Account.SObjectType)});
   ```
   The test gets an instance of `IAccountsService` through the DI framework and calls its `processAccounts` method with a synthetic Account ID. The implementation is expected to query for Account records using the selector.

3. **Verification**:
   ```java
   System.assertEquals(1, mockSelector.selectById().size());
   ```
   This assertion verifies that the service called the selector's `selectById` method, which is a key expectation of the test. The mock implementation returns a test Account record.

4. **Mock Implementation**:
   The inner class `MockAccountsSelector` provides a controlled implementation that doesn't touch the database but returns predictable test data.

The key benefits demonstrated by this test approach:

- **Isolation**: It tests the service logic in isolation from the database and other dependencies
- **Speed**: Without database operations, the test runs quickly
- **Predictability**: Using mocks ensures consistent test behavior
- **Verification**: It can verify that the service interacts correctly with its dependencies

This approach is particularly valuable in AT4DX's modular architecture, as it allows testing components without requiring their actual dependencies to be present, which is essential when working across package boundaries.

`AccountsService.processAccounts(AccountIDs)` likely does the following:
1. Takes a set of Account IDs
2. Uses the selector to query for those Accounts
3. Performs some processing on them (which isn't being verified in this specific test)

The test is focused on verifying the interactions between components rather than the end-to-end behavior, which is characteristic of proper unit testing.

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
