import React from 'react';

const Analytics: React.FC = () => {
  return (
    <div className="space-y-6">
      <div className="bg-white rounded-lg shadow p-6">
        <h2 className="text-xl font-semibold mb-4">Analytics Dashboard</h2>
        
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div className="bg-white rounded-lg p-4 border">
            <h3 className="text-lg font-medium mb-4">User Growth & Revenue</h3>
            <div className="h-80 bg-gray-100 flex items-center justify-center">
              <p>Chart Placeholder</p>
            </div>
          </div>
          
          <div className="bg-white rounded-lg p-4 border">
            <h3 className="text-lg font-medium mb-4">Plan Distribution</h3>
            <div className="h-80 bg-gray-100 flex items-center justify-center">
              <p>Chart Placeholder</p>
            </div>
          </div>
        </div>
      </div>
      
      <div className="bg-white rounded-lg shadow p-6">
        <h2 className="text-xl font-semibold mb-4">Key Metrics</h2>
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <div className="bg-blue-50 p-4 rounded-lg border border-blue-200">
            <h3 className="text-sm font-medium text-blue-800">Total Users</h3>
            <p className="text-2xl font-bold">1,245</p>
            <p className="text-sm text-blue-600">↑ 12% from last month</p>
          </div>
          <div className="bg-green-50 p-4 rounded-lg border border-green-200">
            <h3 className="text-sm font-medium text-green-800">Revenue</h3>
            <p className="text-2xl font-bold">$12,450</p>
            <p className="text-sm text-green-600">↑ 8% from last month</p>
          </div>
          <div className="bg-purple-50 p-4 rounded-lg border border-purple-200">
            <h3 className="text-sm font-medium text-purple-800">Active Plans</h3>
            <p className="text-2xl font-bold">3</p>
            <p className="text-sm text-purple-600">No change from last month</p>
          </div>
          <div className="bg-yellow-50 p-4 rounded-lg border border-yellow-200">
            <h3 className="text-sm font-medium text-yellow-800">Avg. Session</h3>
            <p className="text-2xl font-bold">24 min</p>
            <p className="text-sm text-yellow-600">↑ 3% from last month</p>
          </div>
        </div>
      </div>
      
      <div className="bg-white rounded-lg shadow p-6">
        <h2 className="text-xl font-semibold mb-4">AI-Powered Insights</h2>
        <div className="p-4 bg-gray-50 rounded-lg border">
          <div className="flex items-start space-x-4">
            <div className="bg-gray-100 p-2 rounded-full">
              <svg xmlns="http://www.w3.org/2000/svg" className="h-6 w-6 text-gray-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
              </svg>
            </div>
            <div>
              <h3 className="font-medium">Growth Opportunity</h3>
              <p className="mt-1">
                Based on your current user growth rate, we recommend focusing on the Premium plan marketing. 
                Users who start with the Basic plan are 45% more likely to upgrade when offered a 14-day trial of Premium features.
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Analytics;
